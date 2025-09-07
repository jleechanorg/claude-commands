#!/usr/bin/env python3
"""
Simple inline import detector and optimizer.
Recreated from previous session for Phase 2 MVP Core optimization.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class SimpleInlineDetector:
    def __init__(self):
        self.inline_imports = []

    def visit_file(self, filepath: str) -> List[Dict]:
        """Detect inline imports in a Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=filepath)
            detector = InlineImportVisitor(filepath)
            detector.visit(tree)
            return detector.inline_imports

        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return []

    def find_mvp_core_imports(self) -> List[Dict]:
        """Find inline imports in MVP site core files."""
        mvp_files = []
        mvp_path = Path("mvp_site")

        if not mvp_path.exists():
            return []

        # Focus on core Python files, exclude tests
        for py_file in mvp_path.rglob("*.py"):
            if "test" not in str(py_file).lower():
                mvp_files.append(str(py_file))

        all_imports = []
        for filepath in mvp_files:
            imports = self.visit_file(filepath)
            all_imports.extend(imports)

        return all_imports


class InlineImportVisitor(ast.NodeVisitor):
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
                    'priority': self._get_priority(alias.name)
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
                    'priority': self._get_priority(module or alias.name)
                })

    def _get_priority(self, module_name: str) -> str:
        """Classify import priority - HIGH for stdlib modules."""
        stdlib_modules = {
            'sys', 'os', 'json', 'time', 'datetime', 're', 'argparse',
            'subprocess', 'pathlib', 'collections', 'itertools', 'functools',
            'logging', 'typing', 'socket', 'tempfile', 'shutil', 'glob'
        }

        if module_name.split('.')[0] in stdlib_modules:
            return 'HIGH'
        elif module_name.startswith(('mvp_site', 'scripts')):
            return 'MEDIUM'
        else:
            return 'LOW'


def main():
    detector = SimpleInlineDetector()
    imports = detector.find_mvp_core_imports()

    if not imports:
        print("No inline imports found in MVP core files.")
        return

    print(f"Found {len(imports)} inline imports in MVP core:")

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
            for imp in by_priority[priority][:10]:  # Show first 10
                print(f"  {imp['file']}:{imp['line']} - {imp.get('module', 'unknown')}")

    return imports


if __name__ == '__main__':
    main()
