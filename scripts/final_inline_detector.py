#!/usr/bin/env python3
"""
Phase 4: Final comprehensive inline import detector.
Finds ALL remaining inline imports for final cleanup.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict


class FinalInlineDetector:
    def __init__(self):
        self.inline_imports = []

    def find_all_inline_imports(self) -> List[Dict]:
        """Find ALL remaining inline imports in the codebase."""
        all_files = []

        # Scan key directories
        for directory in ["mvp_site", "scripts", "testing_ui"]:
            path = Path(directory)
            if path.exists():
                for py_file in path.rglob("*.py"):
                    all_files.append(str(py_file))

        all_imports = []
        for filepath in all_files:
            imports = self.visit_file(filepath)
            all_imports.extend(imports)

        return all_imports

    def visit_file(self, filepath: str) -> List[Dict]:
        """Detect inline imports in a Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=filepath)
            detector = FinalInlineImportVisitor(filepath)
            detector.visit(tree)
            return detector.inline_imports

        except Exception as e:
            print(f"Warning: Error processing {filepath}: {e}")
            return []


class FinalInlineImportVisitor(ast.NodeVisitor):
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
                # Determine base complexity, but force 'COMPLEX' if the import uses an alias
                complexity = self._get_complexity(alias.name)
                if alias.asname:
                    complexity = 'COMPLEX'

                self.inline_imports.append({
                    'file': self.filepath,
                    'line': node.lineno,
                    'type': 'import',
                    'module': alias.name,
                    'asname': alias.asname,
                    'depth': self.function_depth,
                    'priority': self._get_priority(alias.name),
                    'complexity': complexity
                })

    def visit_ImportFrom(self, node):
        if self.in_function:
            module = node.module or ''
            for alias in node.names:
                # Determine base complexity, but force 'COMPLEX' if the import uses an alias
                complexity = self._get_complexity(module or alias.name)
                if alias.asname:
                    complexity = 'COMPLEX'

                self.inline_imports.append({
                    'file': self.filepath,
                    'line': node.lineno,
                    'type': 'from_import',
                    'module': f"{module}.{alias.name}" if module else alias.name,
                    'from_module': module,
                    'import_name': alias.name,
                    'asname': alias.asname,
                    'depth': self.function_depth,
                    'priority': self._get_priority(module or alias.name),
                    'complexity': complexity
                })

    def _get_priority(self, module_name: str) -> str:
        """Classify import priority."""
        # HIGH: Standard library modules
        stdlib_modules = {
            'sys', 'os', 'json', 'time', 'datetime', 're', 'argparse',
            'subprocess', 'pathlib', 'collections', 'itertools', 'functools',
            'logging', 'typing', 'socket', 'tempfile', 'shutil', 'glob',
            'unittest', 'pytest', 'mock', 'io', 'random'
        }

        module_base = module_name.split('.')[0]

        if module_base in stdlib_modules:
            return 'HIGH'
        elif module_name.startswith(('mvp_site', 'scripts')):
            return 'MEDIUM'
        else:
            return 'LOW'

    def _get_complexity(self, module_name: str) -> str:
        """Classify complexity of fixing the import."""
        # SIMPLE: Easy to move to top
        simple_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 're', 'tempfile',
            'pathlib', 'collections', 'logging', 'typing'
        }

        # CONDITIONAL: May be conditional imports
        conditional_patterns = {
            'unittest.mock', 'pytest', 'google.', 'firebase_', 'argparse'
        }

        # COMPLEX: Likely conditional or special handling
        complex_patterns = {
            'http.server', 'threading', 'uuid', 'firestore_service',
            'world_logic', 'firebase_utils'
        }

        module_base = module_name.split('.')[0]

        if module_base in simple_modules:
            return 'SIMPLE'
        elif any(pattern in module_name for pattern in conditional_patterns):
            return 'CONDITIONAL'
        elif any(pattern in module_name for pattern in complex_patterns):
            return 'COMPLEX'
        else:
            return 'MEDIUM'


def get_top_level_imports(source_code: str) -> set:
    """Use AST to get all top-level import statements."""
    try:
        tree = ast.parse(source_code)
    except Exception:
        return set()
    imports = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            # Handle relative imports
            module = node.module if node.module else ""
            for alias in node.names:
                imports.add(f"from {module} import {alias.name}")
    return imports


def fix_simple_imports(imports: List[Dict]) -> int:
    """Fix SIMPLE priority imports that can be safely moved."""
    fixed_count = 0

    # Group by file
    by_file = {}
    for imp in imports:
        if imp['complexity'] == 'SIMPLE' and imp['priority'] == 'HIGH':
            filepath = imp['file']
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append(imp)

    for filepath, file_imports in by_file.items():
        if fix_file_simple_imports(filepath, file_imports):
            fixed_count += 1

    return fixed_count


def fix_file_simple_imports(filepath: str, imports: List[Dict]) -> bool:
    """Fix simple inline imports in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # Collect unique imports to add
        imports_to_add = set()
        for imp in imports:
            if imp['type'] == 'import':
                imports_to_add.add(f"import {imp['module']}")
            else:
                imports_to_add.add(f"from {imp['from_module']} import {imp['import_name']}")

        # Find insertion point after existing imports
        insert_pos = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                insert_pos = i + 1
            elif stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                if insert_pos > 0:
                    break
                else:
                    insert_pos = i
                    break

        # Add missing imports using AST-based detection
        existing_imports = get_top_level_imports(content)
        new_imports = []
        for import_line in sorted(imports_to_add):
            if import_line not in existing_imports:
                new_imports.append(import_line)

        if new_imports:
            # First, remove inline imports (before inserting new ones to avoid line number shifts)
            for imp in imports:
                line_num = imp['line'] - 1  # Convert to 0-based
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    original_indent = line[:len(line) - len(line.lstrip())]
                    if imp['type'] == 'import' and line.strip().startswith('import '):
                        lines[line_num] = f"{original_indent}# Moved import to top-level"
                    elif imp['type'] == 'from_import' and line.strip().startswith('from '):
                        lines[line_num] = f"{original_indent}# Moved import to top-level"

            # Then insert new imports at the top
            for i, import_line in enumerate(new_imports):
                lines.insert(insert_pos + i, import_line)

            new_content = '\n'.join(lines)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"Fixed {len(new_imports)} simple imports in {filepath}")
            return True

        return False

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def main():
    """Main execution for Phase 4 final import optimization."""
    print("Phase 4: Final comprehensive inline import scan...")

    detector = FinalInlineDetector()
    imports = detector.find_all_inline_imports()

    if not imports:
        print("No inline imports found.")
        return 0

    print(f"Found {len(imports)} total inline imports:")

    # Group by priority and complexity
    stats = {
        'HIGH_SIMPLE': [],
        'HIGH_CONDITIONAL': [],
        'HIGH_COMPLEX': [],
        'MEDIUM': [],
        'LOW': []
    }

    for imp in imports:
        priority = imp['priority']
        complexity = imp['complexity']

        if priority == 'HIGH':
            key = f"HIGH_{complexity}"
            if key in stats:
                stats[key].append(imp)
            else:
                stats['HIGH_COMPLEX'].append(imp)
        else:
            stats[priority].append(imp)

    # Display summary
    print("\n📊 IMPORT ANALYSIS:")
    for category, items in stats.items():
        if items:
            print(f"\n{category} ({len(items)} imports):")
            for imp in items[:3]:  # Show first 3
                print(f"  {imp['file']}:{imp['line']} - {imp.get('module', 'unknown')}")
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more")

    # Fix SIMPLE HIGH priority imports
    simple_high = stats.get('HIGH_SIMPLE', [])
    if simple_high:
        print(f"\n🔧 Fixing {len(simple_high)} SIMPLE HIGH priority imports...")
        fixed_count = fix_simple_imports(simple_high)
        print(f"Fixed imports in {fixed_count} files.")

    return len(imports)


if __name__ == '__main__':
    sys.exit(main())
