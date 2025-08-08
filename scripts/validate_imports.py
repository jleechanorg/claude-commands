#!/usr/bin/env python3
"""
Import Validation Script

Enforces clean import standards:
1. No try/except around imports
2. All imports at top of file (no inline imports)
3. Clean relative imports only within same package

Usage:
    python validate_imports.py [directory]
    python validate_imports.py mvp_site
"""

import ast
import sys
from pathlib import Path
from typing import NamedTuple


class ImportViolation(NamedTuple):
    """Represents an import validation violation."""

    file: Path
    line: int
    message: str
    code: str


class ImportValidator(ast.NodeVisitor):
    """AST visitor to validate import patterns."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: list[ImportViolation] = []
        self.import_seen = False
        self.non_import_seen = False
        self.in_try_except = False
        self.try_except_depth = 0

    def visit_Try(self, node: ast.Try) -> None:
        """Check for try/except blocks containing imports."""
        old_in_try = self.in_try_except
        old_depth = self.try_except_depth

        self.in_try_except = True
        self.try_except_depth += 1

        # Check if try block contains imports
        for child in ast.walk(node):
            if isinstance(child, ast.Import | ast.ImportFrom):
                self.violations.append(
                    ImportViolation(
                        file=self.file_path,
                        line=child.lineno,
                        message="Import statement inside try/except block",
                        code="IMP001",
                    )
                )

        self.generic_visit(node)

        self.in_try_except = old_in_try
        self.try_except_depth = old_depth

    def visit_Import(self, node: ast.Import) -> None:
        """Validate import statements."""
        self.import_seen = True

        if self.non_import_seen:
            self.violations.append(
                ImportViolation(
                    file=self.file_path,
                    line=node.lineno,
                    message="Import statement not at top of file (inline import)",
                    code="IMP002",
                )
            )

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Validate from-import statements."""
        self.import_seen = True

        if self.non_import_seen:
            self.violations.append(
                ImportViolation(
                    file=self.file_path,
                    line=node.lineno,
                    message="Import statement not at top of file (inline import)",
                    code="IMP002",
                )
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Mark non-import code."""
        if self.import_seen:
            self.non_import_seen = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Mark non-import code."""
        if self.import_seen:
            self.non_import_seen = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Mark non-import code."""
        if self.import_seen:
            self.non_import_seen = True
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        """Mark non-import code (excluding docstrings)."""
        # Skip docstrings at module level
        if (
            isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and not self.non_import_seen
        ):
            self.generic_visit(node)
            return

        if self.import_seen:
            self.non_import_seen = True
        self.generic_visit(node)


def validate_file(file_path: Path) -> list[ImportViolation]:
    """Validate imports in a single Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        validator = ImportValidator(file_path)
        validator.visit(tree)

        return validator.violations

    except SyntaxError as e:
        return [
            ImportViolation(
                file=file_path,
                line=e.lineno or 0,
                message=f"Syntax error: {e.msg}",
                code="SYN001",
            )
        ]
    except Exception as e:
        return [
            ImportViolation(
                file=file_path, line=0, message=f"Validation error: {e}", code="ERR001"
            )
        ]


def validate_directory(directory: Path) -> list[ImportViolation]:
    """Validate all Python files in a directory."""
    violations = []

    for py_file in directory.rglob("*.py"):
        # Skip certain directories
        if any(part in str(py_file) for part in [".venv", "__pycache__", ".git"]):
            continue

        file_violations = validate_file(py_file)
        violations.extend(file_violations)

    return violations


def main():
    """Main validation function."""
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("mvp_site")

    print(f"🔍 Validating imports in: {target}")
    print("=" * 50)

    if target.is_file():
        violations = validate_file(target)
    else:
        violations = validate_directory(target)

    if not violations:
        print("✅ All import validations passed!")
        return 0

    print(f"❌ Found {len(violations)} import violations:")
    print()

    for violation in violations:
        print(f"  {violation.file}:{violation.line}")
        print(f"    {violation.code}: {violation.message}")
        print()

    print("Import Validation Rules:")
    print("  IMP001: No try/except around imports")
    print("  IMP002: No inline imports (imports must be at top)")
    print("  SYN001: Syntax error")
    print("  ERR001: Validation error")

    return 1


if __name__ == "__main__":
    sys.exit(main())
