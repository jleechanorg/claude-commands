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

        # Find test files in mvp_site/tests following project policy
        mvp_tests_path = Path("mvp_site/tests")
        if mvp_tests_path.exists():
            for py_file in mvp_tests_path.glob("test_*.py"):
                test_files.append(str(py_file))

        # Also check root tests directory if exists
        tests_path = Path("tests")
        if tests_path.exists():
            for py_file in tests_path.glob("test_*.py"):
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


def _get_existing_imports(content: str) -> List[str]:
    """Extract existing imports from file content using AST."""
    try:
        tree = ast.parse(content)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module:
                        imports.append(f"from {module} import {alias.name}")
                    else:
                        imports.append(f"from . import {alias.name}")
        return imports
    except Exception:
        return []


def _import_already_exists(import_line: str, existing_imports: List[str]) -> bool:
    """Check if import already exists using exact matching."""
    return import_line in existing_imports


def _remove_inline_imports(content: str, imports: List[Dict]) -> str:
    """Remove inline imports using AST-based approach."""
    try:
        lines = content.split('\n')
        lines_to_remove = set()

        # Collect line numbers of inline imports to remove
        for imp in imports:
            line_num = imp['line'] - 1  # Convert to 0-based index
            if 0 <= line_num < len(lines):
                line = lines[line_num].strip()
                # Verify this is actually the import line we expect
                if imp['type'] == 'import' and line.startswith(f"import {imp['module']}"):
                    lines_to_remove.add(line_num)
                elif imp['type'] == 'from_import':
                    from_module = imp.get('from_module', '')
                    import_name = imp['import_name']
                    if from_module and line.startswith(f"from {from_module} import {import_name}"):
                        lines_to_remove.add(line_num)
                    elif not from_module and line.startswith(f"from . import {import_name}"):
                        lines_to_remove.add(line_num)

        # Remove lines in reverse order to maintain indices
        for line_num in sorted(lines_to_remove, reverse=True):
            del lines[line_num]

        return '\n'.join(lines)

    except Exception:
        # Fallback to original content if AST processing fails
        return content


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
                from_module = imp.get('from_module', '')
                if from_module:
                    imports_to_add.add(f"from {from_module} import {imp['import_name']}")
                else:
                    # Handle relative imports
                    imports_to_add.add(f"from . import {imp['import_name']}")

        # Find insertion point (after docstring and existing imports)
        insert_pos = find_test_import_position(lines)

        # Add missing imports using AST to check if already exists
        new_imports = []
        existing_imports = _get_existing_imports(content)
        for import_line in sorted(imports_to_add):
            if not _import_already_exists(import_line, existing_imports):
                new_imports.append(import_line)

        if new_imports:
            # Insert new imports
            for i, import_line in enumerate(new_imports):
                lines.insert(insert_pos + i, import_line)

            # Remove inline imports using AST-based approach
            content = _remove_inline_imports('\n'.join(lines), imports)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Fixed {len(new_imports)} imports in {filepath}")
            return True

        return False

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def find_test_import_position(lines: List[str]) -> int:
    """Find the best position to insert imports in a test file using AST."""
    try:
        content = '\n'.join(lines)
        tree = ast.parse(content)

        # Find the position after module docstring and before first statement
        insert_line = 1  # Default to line 1 (0-indexed)

        # Skip module docstring if present
        if (tree.body and isinstance(tree.body[0], ast.Expr) and
            isinstance(tree.body[0].value, ast.Constant) and
            isinstance(tree.body[0].value.value, str)):
            insert_line = tree.body[0].end_lineno

        # Find last import statement
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                insert_line = node.end_lineno
            elif not isinstance(node, ast.Expr):  # Non-docstring, non-import
                break

        return insert_line

    except Exception:
        # Fallback to simple approach
        insert_pos = 0
        in_docstring = False
        docstring_delim = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle docstrings properly
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                docstring_delim = stripped[:3]
                in_docstring = True
                # Check if docstring ends on same line
                if stripped.count(docstring_delim) >= 2:
                    in_docstring = False
                    insert_pos = i + 1
                continue
            elif in_docstring and docstring_delim and stripped.endswith(docstring_delim):
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
