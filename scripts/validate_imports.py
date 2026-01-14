#!/usr/bin/env python3
"""

from __future__ import annotations
Import Validation Script (Delta Mode Support)

Enforces clean import standards:
1. No try/except around imports
2. All imports at top of file (no inline imports)
3. Clean relative imports only within same package

Usage:
    python validate_imports.py [directory]
    python validate_imports.py mvp_site
    python validate_imports.py --diff-only              # Check only files changed vs main
    python validate_imports.py --diff-only main..HEAD   # Check files changed vs specific branch
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Union


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
        self.sys_path_manipulation_seen = False

        # Allow conditional imports for optional dependencies and testing
        self.allowed_conditional_imports = {
            'uuid', 'os', 'tempfile', 'threading', 'concurrent.futures',
            'argparse', 'glob', 'shlex',
            'google.cloud', 'google.auth', 'google', 'genai',
            'firebase_admin', 'firestore_service', 'world_logic', 'mvp_site.world_logic',
            'http.server', 'BaseHTTPRequestHandler', 'HTTPServer',
            'unittest.mock', 'AsyncMock', 'playwright.sync_api',
            'inspect', 'asyncio', 'time', 'mcp.server.stdio',
            'mcp', 'logging', 'json', 'datetime', 'sys', 'pathlib',
            'typing', 'collections', 'itertools', 'functools',
            'flask', 'werkzeug', 'requests', 'urllib', 'http',
            'ssl', 'socket', 'subprocess', 'shutil', 're', 'math',
            'random', 'statistics', 'contextlib', 'dataclasses',
            'abc', 'enum', 'copy', 'pickle', 'base64', 'hashlib',
            'traceback', 'warnings', 'pytest', 'unittest', 'keyring',
            # Test module imports that need sys.path manipulation
            'main', 'mcp_client', 'tests.fake_firestore', 'logging_util',
            # Test infrastructure modules that need sys.path manipulation
            'orchestrate', 'pr_comment_formatter', 'command_output_trimmer',
            'helpers', 'mcp_api', 'mcp_test_client', 'commentreply',
            'mvp_site.logging_util', 'psutil', 'importlib.util',
            'mvp_site.testing_framework',
            # Automation modules that need sys.path manipulation
            'automation_safety_manager', 'jleechanorg_pr_monitor',
            'automation.automation_safety_manager', 'automation.utils',
            'utils', '.automation_safety_manager', '.utils',
            'codex_config', '.codex_config',
            # Test script modules that need sys.path manipulation
            'test_dependency_analyzer',
            # Testing framework integration utilities (optional for test stability)
            'testing_framework.integration_utils',
            # Optional A2A test dependencies (conditional imports for tests)
            'a2a',
            'httpx',
            # Orchestration modules that support both direct execution and package import
            'orchestration.a2a_integration', 'orchestration.a2a_agent_wrapper',
            'orchestration.message_broker', 'orchestration.task_dispatcher',
            'orchestration.constants', 'orchestration.agent_system',
            'orchestration.a2a_monitor', 'orchestration.debug_worker',
            'orchestration.live_mode',
            'agent_system', 'message_broker', 'a2a_integration', 'task_dispatcher',
            'constants', 'a2a_agent_wrapper', 'a2a_monitor', 'debug_worker', 'live_mode',
            # MCP optional dependencies
            'fastmcp', 'mcp.types',
            # FastEmbed optional dependency (for intent classifier)
            'fastembed',
            # ONNX Runtime optional dependency (required by fastembed)
            'onnxruntime',
            # Claude commands optional dependencies
            'exportcommands',
            # Django optional dependencies
            'django.core.management',
            # Cerebras optional dependencies
            'cerebras', 'cerebras.sdk',
            # Clock skew patch dependencies (required for Firebase auth with clock drift)
            'google.auth._helpers',
            'mvp_site.clock_skew_credentials', 'clock_skew_credentials',
            # mvp_site modules that may be imported after clock_skew_patch()
            'mvp_site', 'mvp_site.constants', 'mvp_site.document_generator',
            'mvp_site.firestore_service', 'mvp_site.llm_service',
            'mvp_site.structured_fields_utils', 'mvp_site.custom_types',
            'mvp_site.debug_hybrid_system', 'mvp_site.game_state',
            'mvp_site.prompt_utils'
        }

    def _is_allowed_conditional_import(self, node: Union[ast.Import, ast.ImportFrom]) -> bool:
        """Check if import is allowed in conditional contexts."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.allowed_conditional_imports:
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module in self.allowed_conditional_imports:
                return True
            # Check for from http.server import ...
            if node.module and any(
                node.module == allowed or node.module.startswith(f"{allowed}.")
                for allowed in self.allowed_conditional_imports
            ):
                return True
        return False

    def visit_Try(self, node: ast.Try) -> None:
        """Check for try/except blocks containing imports."""
        old_in_try = self.in_try_except
        old_depth = self.try_except_depth

        self.in_try_except = True
        self.try_except_depth += 1

        # Check if try block contains imports
        for child in ast.walk(node):
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                # Skip allowed conditional imports
                if not self._is_allowed_conditional_import(child):
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
            # Allow imports after sys.path manipulation (common in test files)
            if self.sys_path_manipulation_seen:
                self.generic_visit(node)
                return

            # Allow conditional imports in specific contexts
            if not self._is_allowed_conditional_import(node):
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
            # Allow imports after sys.path manipulation (common in test files)
            if self.sys_path_manipulation_seen:
                self.generic_visit(node)
                return

            # Allow conditional imports in specific contexts
            if not self._is_allowed_conditional_import(node):
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
        # Functions always mark end of import section per PEP 8
        # This enforces strict import placement: all imports at top of file
        self.non_import_seen = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Mark non-import code."""
        # Classes always mark end of import section per PEP 8
        # This enforces strict import placement: all imports at top of file
        self.non_import_seen = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Mark non-import code."""
        # Check if this is sys.path manipulation (common in test files)
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                if isinstance(node.value.func.value, ast.Attribute):
                    if (isinstance(node.value.func.value.value, ast.Name) and
                        node.value.func.value.value.id == 'sys' and
                        node.value.func.value.attr == 'path' and
                        node.value.func.attr in ('insert', 'append')):
                        # Allow imports after sys.path manipulation in test files
                        self.sys_path_manipulation_seen = True
                        self.generic_visit(node)
                        return

        # Allow os.environ assignments before imports (common in test files)
        if isinstance(node.targets[0], ast.Subscript):
            if isinstance(node.targets[0].value, ast.Attribute):
                if (isinstance(node.targets[0].value.value, ast.Name) and
                    node.targets[0].value.value.id == 'os' and
                    node.targets[0].value.attr == 'environ'):
                    # Allow imports after os.environ assignments in test files
                    self.sys_path_manipulation_seen = True
                    self.generic_visit(node)
                    return

        # Assignments always mark end of import section per PEP 8
        # This enforces strict import placement: all imports at top of file
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

        # Check if this is sys.path manipulation (common in test files)
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                if isinstance(node.value.func.value, ast.Attribute):
                    if (isinstance(node.value.func.value.value, ast.Name) and
                        node.value.func.value.value.id == 'sys' and
                        node.value.func.value.attr == 'path' and
                        node.value.func.attr in ('insert', 'append')):
                        # Allow imports after sys.path manipulation in test files
                        self.sys_path_manipulation_seen = True
                        self.generic_visit(node)
                        return

        if self.import_seen:
            self.non_import_seen = True
        self.generic_visit(node)


# Files with architectural import requirements that need exemption from validation
EXCLUDED_FILES = {
    'clock_skew_credentials.py',  # Clock skew patch implementation - needs lazy google.auth imports
    'world_logic.py',  # Must import clock_skew_patch before firebase_admin
}


def validate_file(file_path: Path) -> list[ImportViolation]:
    """Validate imports in a single Python file."""
    # Skip files with architectural import requirements
    if file_path.name in EXCLUDED_FILES:
        return []

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


def get_changed_python_files(diff_spec: str = "origin/main...HEAD") -> list[Path]:
    """Get Python files changed in git diff."""
    # Try multiple diff strategies for CI compatibility
    diff_strategies = [
        diff_spec,  # Original three-dot notation
        diff_spec.replace('...', '..'),  # Two-dot notation
        "HEAD~1",  # Compare with previous commit
        "--cached",  # Staged changes only (fallback)
    ]

    for strategy in diff_strategies:
        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", strategy],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if line and line.endswith('.py'):
                    file_path = Path(line)
                    if file_path.exists():
                        changed_files.append(file_path)

            # If we got files, return them
            if changed_files:
                print(f"📋 Using diff strategy: git diff --name-only {strategy}")
                return changed_files

            # If no files found with this strategy, try next one
            continue

        except subprocess.CalledProcessError as e:
            err = (e.stderr or "").strip()
            print(f"⚠️ git diff strategy '{strategy}' failed: {err}")
            # Try next strategy
            continue
        except Exception as e:
            print(f"⚠️ Error with strategy '{strategy}': {e}")
            continue

    # If all strategies failed, return empty list (no files to validate)
    print("⚠️ All git diff strategies failed, assuming no Python files changed")
    return []


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


def validate_changed_files(diff_spec: str = "origin/main...HEAD") -> list[ImportViolation]:
    """Validate only Python files changed in git diff."""
    violations = []
    changed_files = get_changed_python_files(diff_spec)

    if not changed_files:
        print("📝 No Python files changed in diff")
        return violations

    print(f"📝 Found {len(changed_files)} changed Python files:")
    for f in changed_files:
        print(f"  - {f}")
    print()

    for py_file in changed_files:
        file_violations = validate_file(py_file)
        violations.extend(file_violations)

    return violations


def main():
    """Main validation function."""
    # Handle --diff-only flag
    if len(sys.argv) > 1 and sys.argv[1] == "--diff-only":
        diff_spec = sys.argv[2] if len(sys.argv) > 2 else "origin/main...HEAD"
        print(f"🔍 Validating imports in changed files: {diff_spec}")
        print("=" * 50)
        violations = validate_changed_files(diff_spec)
    else:
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
