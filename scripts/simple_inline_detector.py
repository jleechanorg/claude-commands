#!/usr/bin/env python3
"""
Simple Inline Import Detector
Quickly scan Python files for inline imports and generate actionable reports.
"""

import ast
import glob
import os
import sys
from dataclasses import dataclass


@dataclass
class InlineImportInfo:
    file_path: str
    line_number: int
    import_statement: str
    context: str
    severity: str


class QuickInlineDetector(ast.NodeVisitor):
    """Fast AST visitor for detecting inline imports."""

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.inline_imports = []
        self.context_depth = 0
        self.in_function = False
        self.in_class = False
        self.in_conditional = False

    def visit_FunctionDef(self, node):
        prev_in_function = self.in_function
        self.in_function = True
        self.context_depth += 1
        self.generic_visit(node)
        self.context_depth -= 1
        self.in_function = prev_in_function

    def visit_AsyncFunctionDef(self, node):
        prev_in_function = self.in_function
        self.in_function = True
        self.context_depth += 1
        self.generic_visit(node)
        self.context_depth -= 1
        self.in_function = prev_in_function

    def visit_ClassDef(self, node):
        prev_in_class = self.in_class
        self.in_class = True
        self.context_depth += 1
        self.generic_visit(node)
        self.context_depth -= 1
        self.in_class = prev_in_class

    def visit_If(self, node):
        prev_in_conditional = self.in_conditional
        self.in_conditional = True
        self.context_depth += 1
        self.generic_visit(node)
        self.context_depth -= 1
        self.in_conditional = prev_in_conditional

    def visit_Try(self, node):
        self.context_depth += 1
        self.generic_visit(node)
        self.context_depth -= 1

    def visit_Import(self, node):
        if self.context_depth > 0:
            self._record_inline_import(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self.context_depth > 0:
            self._record_inline_import(node)
        self.generic_visit(node)

    def _record_inline_import(self, node):
        """Record an inline import."""
        import_stmt = self._get_import_statement(node)
        context = self._get_context_description()
        severity = self._get_severity()

        self.inline_imports.append(InlineImportInfo(
            file_path=self.file_path,
            line_number=node.lineno,
            import_statement=import_stmt,
            context=context,
            severity=severity
        ))

    def _get_import_statement(self, node):
        """Reconstruct import statement."""
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            return f"import {', '.join(names)}"
        module = node.module or ""
        names = [alias.name for alias in node.names]
        return f"from {module} import {', '.join(names)}"

    def _get_context_description(self):
        """Describe the context where import was found."""
        contexts = []
        if self.in_function:
            contexts.append("function")
        if self.in_class:
            contexts.append("class")
        if self.in_conditional:
            contexts.append("conditional")
        return "/".join(contexts) if contexts else "nested"

    def _get_severity(self):
        """Determine severity of the inline import."""
        if self.in_function and not self.in_conditional:
            return "HIGH"
        if self.in_conditional:
            return "MEDIUM"
        return "LOW"


def analyze_file(file_path: str) -> list[InlineImportInfo]:
    """Analyze a single Python file for inline imports."""
    try:
        with open(file_path, encoding='utf-8') as f:
            source = f.read()
            source_lines = source.splitlines()

        tree = ast.parse(source)
        detector = QuickInlineDetector(file_path, source_lines)
        detector.visit(tree)
        return detector.inline_imports

    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return []


def find_python_files(paths: list[str]) -> list[str]:
    """Find all Python files in given paths."""
    python_files = []

    for path in paths:
        if os.path.isfile(path) and path.endswith('.py'):
            python_files.append(path)
        elif os.path.isdir(path):
            pattern = os.path.join(path, '**', '*.py')
            python_files.extend(glob.glob(pattern, recursive=True))

    return python_files


def generate_pr_groups(files_with_imports: list[str]) -> dict[str, list[str]]:
    """Group files by logical modules for PR strategy."""
    groups = {
        'scripts': [],
        'mvp_site': [],
        'claude_commands': [],
        'tests': [],
        'other': []
    }

    for file_path in files_with_imports:
        if 'scripts/' in file_path:
            groups['scripts'].append(file_path)
        elif 'mvp_site/' in file_path:
            groups['mvp_site'].append(file_path)
        elif '.claude/' in file_path:
            groups['claude_commands'].append(file_path)
        elif 'test' in file_path:
            groups['tests'].append(file_path)
        else:
            groups['other'].append(file_path)

    return {k: v for k, v in groups.items() if v}  # Remove empty groups


def print_analysis_report(all_imports: list[InlineImportInfo]):
    """Print comprehensive analysis report."""
    if not all_imports:
        print("✅ No inline imports found!")
        return

    print("🔍 INLINE IMPORT ANALYSIS REPORT")
    print(f"{'='*50}")
    print(f"Total inline imports found: {len(all_imports)}")
    print()

    # Group by severity
    severity_counts = {}
    for imp in all_imports:
        severity_counts[imp.severity] = severity_counts.get(imp.severity, 0) + 1

    print("SEVERITY BREAKDOWN:")
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        count = severity_counts.get(severity, 0)
        if count > 0:
            print(f"  {severity}: {count}")
    print()

    # Group by file
    file_groups = {}
    for imp in all_imports:
        if imp.file_path not in file_groups:
            file_groups[imp.file_path] = []
        file_groups[imp.file_path].append(imp)

    print("FILES WITH INLINE IMPORTS:")
    for file_path, imports in sorted(file_groups.items()):
        print(f"\n📄 {file_path} ({len(imports)} imports)")
        for imp in imports:
            print(f"    Line {imp.line_number:3d}: {imp.import_statement:<30} [{imp.severity}] ({imp.context})")

    # PR Grouping Strategy
    print("\n🚀 PR SPLITTING STRATEGY:")
    print(f"{'='*50}")

    files_with_imports = list(file_groups.keys())
    pr_groups = generate_pr_groups(files_with_imports)

    for group_name, files in pr_groups.items():
        if files:
            print(f"\nPR Group: {group_name.upper()} ({len(files)} files)")
            for file_path in files[:5]:  # Show first 5
                count = len(file_groups[file_path])
                print(f"  - {file_path} ({count} imports)")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")

    # Quick Fix Suggestions
    high_priority = [imp for imp in all_imports if imp.severity == 'HIGH']
    if high_priority:
        print(f"\n⚡ QUICK WINS (HIGH Priority - {len(high_priority)} imports):")
        print("These can likely be moved to module level immediately:")

        quick_wins = {}
        for imp in high_priority:
            if imp.file_path not in quick_wins:
                quick_wins[imp.file_path] = []
            quick_wins[imp.file_path].append(imp.import_statement)

        for file_path, imports in sorted(quick_wins.items()):
            print(f"\n  {file_path}:")
            for import_stmt in set(imports):  # Remove duplicates
                print(f"    - {import_stmt}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        paths = ['.']
    else:
        paths = sys.argv[1:]

    print("🔍 Scanning for inline imports...")

    python_files = find_python_files(paths)
    print(f"Found {len(python_files)} Python files to analyze")

    all_imports = []
    files_analyzed = 0

    for file_path in python_files:
        imports = analyze_file(file_path)
        all_imports.extend(imports)
        if imports:
            files_analyzed += 1

    print(f"Analyzed {len(python_files)} files, found issues in {files_analyzed}")
    print()

    print_analysis_report(all_imports)


if __name__ == "__main__":
    main()
