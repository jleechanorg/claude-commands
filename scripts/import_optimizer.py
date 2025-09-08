#!/usr/bin/env python3
"""
Import Optimizer - Automated tool to fix inline imports

This tool can automatically move safe inline imports to module level
and generate PR-ready changes grouped by logical modules.

Usage:
    python import_optimizer.py --analyze [paths...]          # Analysis only
    python import_optimizer.py --fix-safe [paths...]         # Fix HIGH priority only
    python import_optimizer.py --fix-all [paths...]          # Fix all imports
    python import_optimizer.py --generate-prs [paths...]     # Generate PR branches
"""

import ast
import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import tempfile
import shutil
import re

from simple_inline_detector import (
    QuickInlineDetector, InlineImportInfo,
    analyze_file, find_python_files, generate_pr_groups
)


@dataclass
class ImportFix:
    """Represents a proposed import fix."""
    file_path: str
    line_number: int
    import_statement: str
    action: str  # 'move_to_top', 'conditional_move', 'manual_review'
    confidence: str  # 'high', 'medium', 'low'
    risk_factors: List[str]


class ImportOptimizer:
    """Main optimizer that can automatically fix imports."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.manual_review_needed = []

    def analyze_and_fix(self, paths: List[str], fix_mode: str = 'safe') -> Dict:
        """Analyze files and optionally apply fixes."""
        print(f"🔍 Analyzing files in: {', '.join(paths)}")

        python_files = find_python_files(paths)
        all_imports = []

        for file_path in python_files:
            imports = analyze_file(file_path)
            all_imports.extend(imports)

        print(f"Found {len(all_imports)} inline imports across {len(python_files)} files")

        # Generate fixes
        fixes = self._generate_fixes(all_imports, fix_mode)

        if not self.dry_run:
            self._apply_fixes(fixes)

        return {
            'total_imports': len(all_imports),
            'fixes_generated': len(fixes),
            'fixes_applied': len(self.fixes_applied),
            'manual_review': len(self.manual_review_needed),
            'pr_strategy': self._generate_pr_strategy(fixes)
        }

    def _generate_fixes(self, imports: List[InlineImportInfo], fix_mode: str) -> List[ImportFix]:
        """Generate fixes for inline imports."""
        fixes = []

        for imp in imports:
            confidence, action, risk_factors = self._analyze_import_safety(imp)

            # Filter based on fix mode
            if fix_mode == 'safe' and confidence != 'high':
                continue
            elif fix_mode == 'medium' and confidence == 'low':
                continue

            fix = ImportFix(
                file_path=imp.file_path,
                line_number=imp.line_number,
                import_statement=imp.import_statement,
                action=action,
                confidence=confidence,
                risk_factors=risk_factors
            )
            fixes.append(fix)

        return fixes

    def _analyze_import_safety(self, imp: InlineImportInfo) -> Tuple[str, str, List[str]]:
        """Analyze how safe it is to move this import."""
        risk_factors = []

        # Check for obvious safe cases
        if imp.severity == 'HIGH' and 'function' in imp.context:
            # Standard library imports in functions are usually safe
            if self._is_stdlib_import(imp.import_statement):
                return 'high', 'move_to_top', []

            # Check for circular import risks
            if self._check_circular_import_risk(imp):
                risk_factors.append('potential_circular_import')

        # Check for conditional imports
        if 'conditional' in imp.context:
            risk_factors.append('conditional_logic')
            return 'medium', 'conditional_move', risk_factors

        # Check for exception handling imports
        if imp.severity == 'LOW':
            risk_factors.append('exception_handling')
            return 'low', 'manual_review', risk_factors

        # Default case
        confidence = 'high' if imp.severity == 'HIGH' else 'medium'
        action = 'move_to_top' if confidence == 'high' else 'conditional_move'

        return confidence, action, risk_factors

    def _is_stdlib_import(self, import_stmt: str) -> bool:
        """Check if import is from Python standard library."""
        stdlib_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'logging', 'argparse',
            'subprocess', 'shutil', 'pathlib', 'glob', 'tempfile', 'uuid',
            'hashlib', 'threading', 're', 'collections', 'itertools'
        }

        # Extract module name from import statement
        if import_stmt.startswith('import '):
            module = import_stmt.replace('import ', '').split('.')[0].split(',')[0].strip()
        elif import_stmt.startswith('from '):
            module = import_stmt.split(' import ')[0].replace('from ', '').split('.')[0].strip()
        else:
            return False

        return module in stdlib_modules

    def _check_circular_import_risk(self, imp: InlineImportInfo) -> bool:
        """Check for potential circular import issues."""
        # Simple heuristic: local imports (relative or same package)
        if 'from .' in imp.import_statement:
            return True
        if imp.file_path.replace('/', '.').replace('.py', '') in imp.import_statement:
            return True
        return False

    def _apply_fixes(self, fixes: List[ImportFix]) -> None:
        """Apply the import fixes to files."""
        fixes_by_file = {}

        for fix in fixes:
            if fix.file_path not in fixes_by_file:
                fixes_by_file[fix.file_path] = []
            fixes_by_file[fix.file_path].append(fix)

        for file_path, file_fixes in fixes_by_file.items():
            try:
                self._fix_file(file_path, file_fixes)
                self.fixes_applied.extend(file_fixes)
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")
                self.manual_review_needed.extend(file_fixes)

    def _fix_file(self, file_path: str, fixes: List[ImportFix]) -> None:
        """Fix imports in a single file."""
        print(f"🔧 Fixing {file_path}")

        # Read original file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find existing imports section
        import_insert_line = self._find_import_insert_position(lines)

        # Collect imports to add and lines to remove
        imports_to_add = set()
        lines_to_remove = set()

        for fix in fixes:
            if fix.action == 'move_to_top':
                imports_to_add.add(fix.import_statement)
                lines_to_remove.add(fix.line_number - 1)  # Convert to 0-based

        # Remove inline import lines (in reverse order to preserve line numbers)
        for line_idx in sorted(lines_to_remove, reverse=True):
            if line_idx < len(lines):
                # Check if line contains only whitespace and import
                line = lines[line_idx].strip()
                if line.startswith(('import ', 'from ')):
                    lines.pop(line_idx)

        # Add imports at the top
        import_lines = [f"{imp}\n" for imp in sorted(imports_to_add)]

        # Insert new imports
        for i, import_line in enumerate(import_lines):
            lines.insert(import_insert_line + i, import_line)

        # Write fixed file
        if not self.dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

    def _find_import_insert_position(self, lines: List[str]) -> int:
        """Find the best position to insert new imports."""
        # Look for existing imports, docstrings, etc.
        in_docstring = False
        last_import_line = 0
        docstring_end = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Track docstrings
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                if not in_docstring:
                    docstring_end = i + 1

            # Skip comments and empty lines at the top
            if stripped.startswith('#') or not stripped:
                continue

            # Found import
            if stripped.startswith(('import ', 'from ')) and not in_docstring:
                last_import_line = i + 1
            elif stripped and not in_docstring and last_import_line > 0:
                # Found non-import after imports
                break

        # Insert after last import, or after docstring, or at beginning
        return max(last_import_line, docstring_end)

    def _generate_pr_strategy(self, fixes: List[ImportFix]) -> Dict:
        """Generate PR strategy for the fixes."""
        files_with_fixes = list(set(fix.file_path for fix in fixes))
        pr_groups = generate_pr_groups(files_with_fixes)

        strategy = {
            'total_files': len(files_with_fixes),
            'groups': pr_groups,
            'recommended_order': self._get_pr_order(pr_groups),
            'estimated_effort': self._estimate_effort(fixes)
        }

        return strategy

    def _get_pr_order(self, pr_groups: Dict[str, List[str]]) -> List[str]:
        """Recommend order for PR creation."""
        # Start with tests (safest), then utilities, then core code
        order = []

        preferred_order = ['tests', 'scripts', 'claude_commands', 'other', 'mvp_site']

        for group in preferred_order:
            if group in pr_groups:
                order.append(group)

        return order

    def _estimate_effort(self, fixes: List[ImportFix]) -> Dict:
        """Estimate effort for the fixes."""
        by_confidence = {}
        for fix in fixes:
            by_confidence[fix.confidence] = by_confidence.get(fix.confidence, 0) + 1

        return {
            'automatic_fixes': by_confidence.get('high', 0),
            'review_needed': by_confidence.get('medium', 0) + by_confidence.get('low', 0),
            'estimated_time_minutes': len(fixes) * 2  # 2 minutes per fix on average
        }


def create_pr_branches(optimizer_result: Dict) -> None:
    """Create separate branches for each PR group."""
    pr_strategy = optimizer_result['pr_strategy']

    print(f"\n🌿 PR BRANCH CREATION STRATEGY")
    print(f"{'='*50}")

    for i, group in enumerate(pr_strategy['recommended_order']):
        branch_name = f"fix/inline-imports-{group}"
        file_count = len(pr_strategy['groups'][group])

        print(f"\nPR {i+1}: {branch_name}")
        print(f"  Files: {file_count}")
        print(f"  Command: git checkout -b {branch_name}")
        print(f"  Focus: {group.replace('_', ' ').title()} import optimization")

        if group == 'tests':
            print(f"  Note: Start here - safest changes")
        elif group == 'mvp_site':
            print(f"  Note: Save for last - most complex")

    print(f"\nTotal estimated time: {pr_strategy['estimated_effort']['estimated_time_minutes']} minutes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import Optimizer")
    parser.add_argument('paths', nargs='*', default=['.'], help='Paths to analyze')
    parser.add_argument('--analyze', action='store_true', help='Analysis only')
    parser.add_argument('--fix-safe', action='store_true', help='Fix HIGH priority only')
    parser.add_argument('--fix-all', action='store_true', help='Fix all imports')
    parser.add_argument('--generate-prs', action='store_true', help='Generate PR strategy')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Dry run (default)')
    parser.add_argument('--execute', action='store_true', help='Actually apply changes')

    args = parser.parse_args()

    # Determine mode
    if args.fix_safe:
        fix_mode = 'safe'
        dry_run = not args.execute
    elif args.fix_all:
        fix_mode = 'all'
        dry_run = not args.execute
    else:
        fix_mode = 'safe'
        dry_run = True

    optimizer = ImportOptimizer(dry_run=dry_run)

    try:
        result = optimizer.analyze_and_fix(args.paths, fix_mode)

        print(f"\n📊 OPTIMIZATION RESULTS")
        print(f"{'='*50}")
        print(f"Total inline imports found: {result['total_imports']}")
        print(f"Fixes generated: {result['fixes_generated']}")

        if not dry_run:
            print(f"Fixes applied: {result['fixes_applied']}")
        else:
            print(f"Fixes that would be applied: {result['fixes_generated']}")

        print(f"Manual review needed: {result['manual_review']}")

        if args.generate_prs:
            create_pr_branches(result)

        if dry_run and result['fixes_generated'] > 0:
            print(f"\n💡 To actually apply fixes, use --execute")
            print(f"Example: python {sys.argv[0]} --fix-safe --execute {' '.join(args.paths)}")

    except KeyboardInterrupt:
        print(f"\nOptimization interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
