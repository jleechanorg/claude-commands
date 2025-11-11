#!/usr/bin/env python3
"""
Inline Import Detection Tool for Python Projects

This script uses AST parsing to detect and analyze inline imports in Python files,
categorizing them by type and providing actionable recommendations for refactoring.

Usage:
    python detect_inline_imports.py [options] [paths...]

Author: AI Assistant
Created: 2025-01-07
"""

import argparse
import ast
import glob
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ImportType(Enum):
    """Types of inline imports detected."""
    FUNCTION_LEVEL = "function_level"
    CONDITIONAL = "conditional"
    EXCEPTION_HANDLER = "exception_handler"
    CLASS_METHOD = "class_method"
    LOOP_BODY = "loop_body"
    WITH_BLOCK = "with_block"
    NESTED_FUNCTION = "nested_function"


class Severity(Enum):
    """Severity levels for import violations."""
    HIGH = "high"      # Clear violation, should be moved
    MEDIUM = "medium"  # Likely should be moved, but may have reasons
    LOW = "low"        # Edge case, manual review needed


@dataclass
class InlineImport:
    """Represents a detected inline import."""
    file_path: str
    line_number: int
    import_statement: str
    import_type: ImportType
    severity: Severity
    context_lines: list[str]
    parent_function: str | None = None
    parent_class: str | None = None
    reason: str | None = None
    suggestions: list[str] = None


@dataclass
class ModuleAnalysis:
    """Analysis results for a single module."""
    file_path: str
    total_imports: int
    inline_imports: list[InlineImport]
    module_level_imports: list[str]
    suggested_moves: list[str]


@dataclass
class ProjectAnalysis:
    """Complete project analysis results."""
    total_files_analyzed: int
    total_inline_imports: int
    modules: list[ModuleAnalysis]
    pr_grouping_suggestions: dict[str, list[str]]
    summary_by_type: dict[str, int]
    summary_by_severity: dict[str, int]


class InlineImportDetector(ast.NodeVisitor):
    """AST visitor to detect inline imports."""

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.inline_imports: list[InlineImport] = []
        self.module_level_imports: list[str] = []
        self.context_stack: list[dict[str, Any]] = []
        self.current_function: str | None = None
        self.current_class: str | None = None

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        self._analyze_import_node(node, node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statements."""
        self._analyze_import_node(node, node.names)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function context."""
        prev_function = self.current_function
        self.current_function = node.name
        self.context_stack.append({
            'type': 'function',
            'name': node.name,
            'line': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()
        self.current_function = prev_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function context."""
        prev_function = self.current_function
        self.current_function = node.name
        self.context_stack.append({
            'type': 'async_function',
            'name': node.name,
            'line': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()
        self.current_function = prev_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class context."""
        prev_class = self.current_class
        self.current_class = node.name
        self.context_stack.append({
            'type': 'class',
            'name': node.name,
            'line': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()
        self.current_class = prev_class

    def visit_If(self, node: ast.If) -> None:
        """Track conditional context."""
        self.context_stack.append({
            'type': 'conditional',
            'line': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_Try(self, node: ast.Try) -> None:
        """Track try/except context."""
        self.context_stack.append({
            'type': 'try_block',
            'line': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Track exception handler context."""
        self.context_stack.append({
            'type': 'except_handler',
            'line': node.lineno
        })
        self.generic_visit(node)
        self.context_stack.pop()

    def _analyze_import_node(self, node: ast.Import | ast.ImportFrom,
                           names: list[ast.alias]) -> None:
        """Analyze an import node to determine if it's inline."""
        import_statement = self._get_import_statement(node, names)
        line_number = node.lineno

        # Check if this is a module-level import
        if len(self.context_stack) == 0:
            self.module_level_imports.append(import_statement)
            return

        # This is an inline import
        import_type, severity, reason = self._categorize_inline_import()
        context_lines = self._get_context_lines(line_number)
        suggestions = self._generate_suggestions(import_statement, import_type)

        inline_import = InlineImport(
            file_path=self.file_path,
            line_number=line_number,
            import_statement=import_statement,
            import_type=import_type,
            severity=severity,
            context_lines=context_lines,
            parent_function=self.current_function,
            parent_class=self.current_class,
            reason=reason,
            suggestions=suggestions
        )

        self.inline_imports.append(inline_import)

    def _get_import_statement(self, node: ast.Import | ast.ImportFrom,
                            names: list[ast.alias]) -> str:
        """Reconstruct the import statement as string."""
        if isinstance(node, ast.Import):
            imports = ", ".join(alias.name for alias in names)
            return f"import {imports}"
        module = node.module or ""
        level = "." * (node.level or 0)
        imports = ", ".join(
            f"{alias.name} as {alias.asname}" if alias.asname else alias.name
            for alias in names
        )
        return f"from {level}{module} import {imports}"

    def _categorize_inline_import(self) -> tuple[ImportType, Severity, str]:
        """Categorize the inline import based on context."""
        if not self.context_stack:
            return ImportType.FUNCTION_LEVEL, Severity.HIGH, "Module level import"

        current_context = self.context_stack[-1]
        context_type = current_context['type']

        if context_type in ['function', 'async_function']:
            return ImportType.FUNCTION_LEVEL, Severity.HIGH, "Function-level import"
        if context_type == 'conditional':
            return ImportType.CONDITIONAL, Severity.MEDIUM, "Conditional import"
        if context_type in ['try_block', 'except_handler']:
            return ImportType.EXCEPTION_HANDLER, Severity.LOW, "Exception handling import"
        if context_type == 'class':
            return ImportType.CLASS_METHOD, Severity.HIGH, "Class-level import"
        return ImportType.FUNCTION_LEVEL, Severity.MEDIUM, f"Import in {context_type}"

    def _get_context_lines(self, line_number: int, context_size: int = 3) -> list[str]:
        """Get surrounding lines for context."""
        start_line = max(0, line_number - context_size - 1)
        end_line = min(len(self.source_lines), line_number + context_size)
        return self.source_lines[start_line:end_line]

    def _generate_suggestions(self, import_statement: str,
                            import_type: ImportType) -> list[str]:
        """Generate refactoring suggestions."""
        suggestions = []

        if import_type == ImportType.FUNCTION_LEVEL:
            suggestions.append(f"Move '{import_statement}' to module level")
            suggestions.append("Check if import is used in multiple functions")

        elif import_type == ImportType.CONDITIONAL:
            suggestions.append("Consider if this import is truly optional")
            suggestions.append("Move to module level with try/except if needed")

        elif import_type == ImportType.EXCEPTION_HANDLER:
            suggestions.append("Evaluate if this import should be at module level")
            suggestions.append("Consider graceful degradation pattern")

        return suggestions


class InlineImportAnalyzer:
    """Main analyzer class."""

    def __init__(self):
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def analyze_project(self, paths: list[str],
                       patterns: list[str] = None) -> ProjectAnalysis:
        """Analyze entire project for inline imports."""
        if patterns is None:
            patterns = ["*.py"]

        python_files = self._find_python_files(paths, patterns)
        self.logger.info(f"Analyzing {len(python_files)} Python files")

        modules = []
        total_inline_imports = 0

        for file_path in python_files:
            try:
                module_analysis = self._analyze_file(file_path)
                modules.append(module_analysis)
                total_inline_imports += len(module_analysis.inline_imports)
            except Exception as e:
                self.logger.error(f"Error analyzing {file_path}: {e}")
                continue

        pr_suggestions = self._generate_pr_groupings(modules)
        type_summary = self._summarize_by_type(modules)
        severity_summary = self._summarize_by_severity(modules)

        return ProjectAnalysis(
            total_files_analyzed=len(modules),
            total_inline_imports=total_inline_imports,
            modules=modules,
            pr_grouping_suggestions=pr_suggestions,
            summary_by_type=type_summary,
            summary_by_severity=severity_summary
        )

    def _find_python_files(self, paths: list[str],
                          patterns: list[str]) -> list[str]:
        """Find all Python files matching the patterns."""
        python_files = []

        for path in paths:
            if os.path.isfile(path) and path.endswith('.py'):
                python_files.append(path)
            elif os.path.isdir(path):
                for pattern in patterns:
                    full_pattern = os.path.join(path, '**', pattern)
                    python_files.extend(glob.glob(full_pattern, recursive=True))

        return list(set(python_files))  # Remove duplicates

    def _analyze_file(self, file_path: str) -> ModuleAnalysis:
        """Analyze a single Python file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                source_code = f.read()
                source_lines = source_code.splitlines()

            tree = ast.parse(source_code)
            detector = InlineImportDetector(file_path, source_lines)
            detector.visit(tree)

            suggested_moves = [
                imp.import_statement for imp in detector.inline_imports
                if imp.severity in [Severity.HIGH, Severity.MEDIUM]
            ]

            return ModuleAnalysis(
                file_path=file_path,
                total_imports=len(detector.module_level_imports) + len(detector.inline_imports),
                inline_imports=detector.inline_imports,
                module_level_imports=detector.module_level_imports,
                suggested_moves=suggested_moves
            )

        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {e}")
            return ModuleAnalysis(file_path, 0, [], [], [])

    def _generate_pr_groupings(self, modules: list[ModuleAnalysis]) -> dict[str, list[str]]:
        """Generate suggested PR groupings based on logical modules."""
        groupings = {}

        for module in modules:
            if not module.inline_imports:
                continue

            # Group by directory structure
            path_parts = Path(module.file_path).parts

            if 'tests' in path_parts:
                group = 'tests'
            elif 'scripts' in path_parts:
                group = 'scripts'
            elif 'mvp_site' in path_parts:
                group = 'mvp_site'
            elif '.claude' in path_parts:
                group = 'claude_commands'
            else:
                group = 'other'

            if group not in groupings:
                groupings[group] = []
            groupings[group].append(module.file_path)

        return groupings

    def _summarize_by_type(self, modules: list[ModuleAnalysis]) -> dict[str, int]:
        """Summarize imports by type."""
        summary = {}
        for module in modules:
            for imp in module.inline_imports:
                type_name = imp.import_type.value
                summary[type_name] = summary.get(type_name, 0) + 1
        return summary

    def _summarize_by_severity(self, modules: list[ModuleAnalysis]) -> dict[str, int]:
        """Summarize imports by severity."""
        summary = {}
        for module in modules:
            for imp in module.inline_imports:
                severity_name = imp.severity.value
                summary[severity_name] = summary.get(severity_name, 0) + 1
        return summary


class OutputFormatter:
    """Format analysis results for different output types."""

    @staticmethod
    def to_json(analysis: ProjectAnalysis) -> str:
        """Format as JSON."""
        return json.dumps(asdict(analysis), indent=2, default=str)

    @staticmethod
    def to_markdown(analysis: ProjectAnalysis) -> str:
        """Format as Markdown report."""
        md = []
        md.append("# Inline Import Analysis Report\n")

        # Summary
        md.append("## Summary\n")
        md.append(f"- **Files analyzed**: {analysis.total_files_analyzed}")
        md.append(f"- **Total inline imports**: {analysis.total_inline_imports}\n")

        # By type
        md.append("### By Import Type\n")
        for import_type, count in analysis.summary_by_type.items():
            md.append(f"- **{import_type.replace('_', ' ').title()}**: {count}")
        md.append("")

        # By severity
        md.append("### By Severity\n")
        for severity, count in analysis.summary_by_severity.items():
            md.append(f"- **{severity.title()}**: {count}")
        md.append("")

        # PR groupings
        md.append("## Suggested PR Groupings\n")
        for group, files in analysis.pr_grouping_suggestions.items():
            md.append(f"### {group.title()} ({len(files)} files)\n")
            for file_path in files[:10]:  # Limit to first 10
                md.append(f"- `{file_path}`")
            if len(files) > 10:
                md.append(f"- ... and {len(files) - 10} more files")
            md.append("")

        # Detailed findings
        md.append("## Detailed Findings\n")
        for module in analysis.modules:
            if not module.inline_imports:
                continue

            md.append(f"### `{module.file_path}`\n")
            md.append(f"**Total imports**: {module.total_imports} "
                     f"({len(module.inline_imports)} inline)\n")

            for imp in module.inline_imports:
                md.append(f"- **Line {imp.line_number}**: `{imp.import_statement}`")
                md.append(f"  - Type: {imp.import_type.value.replace('_', ' ').title()}")
                md.append(f"  - Severity: {imp.severity.value.title()}")
                if imp.reason:
                    md.append(f"  - Reason: {imp.reason}")
                md.append("")

        return "\n".join(md)

    @staticmethod
    def to_text(analysis: ProjectAnalysis) -> str:
        """Format as plain text."""
        lines = []
        lines.append("INLINE IMPORT ANALYSIS REPORT")
        lines.append("=" * 50)
        lines.append(f"Files analyzed: {analysis.total_files_analyzed}")
        lines.append(f"Total inline imports: {analysis.total_inline_imports}")
        lines.append("")

        # Summary by severity
        lines.append("SEVERITY BREAKDOWN:")
        for severity, count in analysis.summary_by_severity.items():
            lines.append(f"  {severity.upper()}: {count}")
        lines.append("")

        # Files with issues
        lines.append("FILES WITH INLINE IMPORTS:")
        for module in analysis.modules:
            if module.inline_imports:
                lines.append(f"  {module.file_path} ({len(module.inline_imports)} imports)")

        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Detect and analyze inline imports in Python projects"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to analyze (files or directories)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "text"],
        default="markdown",
        help="Output format"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--pattern",
        "-p",
        action="append",
        help="File patterns to include (e.g., *.py)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)

    try:
        analyzer = InlineImportAnalyzer()
        analysis = analyzer.analyze_project(args.paths, args.pattern)

        # Format output
        if args.format == "json":
            output = OutputFormatter.to_json(analysis)
        elif args.format == "markdown":
            output = OutputFormatter.to_markdown(analysis)
        else:  # text
            output = OutputFormatter.to_text(analysis)

        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Analysis written to {args.output}")
        else:
            print(output)

    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
