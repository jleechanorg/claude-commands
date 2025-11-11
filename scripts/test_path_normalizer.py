#!/usr/bin/env python3
"""
Test Path Normalizer for Cross-Platform Compatibility
Fixes Linux/macOS path mismatches and worktree differences in test files.

This utility normalizes path references in test files to work across different
environments, handling common patterns that cause test failures on different platforms.

Usage:
    python3 scripts/test_path_normalizer.py [--test-files pattern] [--dry-run] [--fix-paths]
    python3 scripts/test_path_normalizer.py --scan-failures failing_tests.txt
    python3 scripts/test_path_normalizer.py --normalize-all
"""

import argparse
import logging
import os
import re
import sys
import unittest
from glob import glob
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PathNormalizer:
    """Normalizes test file paths for cross-platform compatibility."""

    def __init__(self, project_root: str = None):
        """Initialize path normalizer with project root detection."""
        self.project_root = self._find_project_root() if not project_root else project_root
        self.platform_patterns = self._get_platform_patterns()
        self.normalization_rules = self._get_normalization_rules()
        self.fixed_files: list[dict] = []
        self.skipped_files: list[dict] = []

    def _find_project_root(self) -> str:
        """Find project root by looking for project markers."""
        current = Path(__file__).parent.absolute()
        while current.parent != current:
            if (current / ".git").exists() or (current / "CLAUDE.md").exists():
                return str(current)
            current = current.parent

        # Fallback to script's grandparent directory
        return str(Path(__file__).parent.parent.absolute())

    def _get_platform_patterns(self) -> dict[str, list[re.Pattern]]:
        """Get regex patterns for different platform-specific issues."""
        return {
            'user_home_paths': [
                re.compile(r'/home/jleechan/(?=projects/)', re.IGNORECASE),
                re.compile(r'/Users/jleechan/(?=projects/)', re.IGNORECASE),
                re.compile(r'C:\\Users\\jleechan\\(?=projects)', re.IGNORECASE),
            ],
            'worktree_names': [
                re.compile(r'/worktree_worker\d+/', re.IGNORECASE),
                re.compile(r'/worktree_tests\d+/', re.IGNORECASE),
                re.compile(r'/worktree[_-]?\w*/', re.IGNORECASE),
            ],
            'path_separators': [
                re.compile(r'\\(?=[^\\]*$)', re.IGNORECASE),  # Windows backslashes at end
                re.compile(r'\\(?=[^\\]*/)', re.IGNORECASE),   # Windows backslashes in middle
            ],
            'absolute_project_paths': [
                re.compile(r'["\']?/[^"\']*worldarchitect\.ai[^"\']*["\']?', re.IGNORECASE),
                re.compile(r'["\']?C:\\[^"\']*worldarchitect\.ai[^"\']*["\']?', re.IGNORECASE),
            ],
            'temp_directory_paths': [
                re.compile(r'/tmp/[^/]*worldarchitect[^/]*/', re.IGNORECASE),
                re.compile(r'C:\\temp\\[^\\]*worldarchitect[^\\]*\\', re.IGNORECASE),
            ]
        }

    def _get_normalization_rules(self) -> dict[str, dict]:
        """Get normalization rules for different types of path issues."""
        return {
            'user_home_replacement': {
                'description': 'Replace absolute user home paths with relative paths',
                'patterns': self.platform_patterns['user_home_paths'],
                'replacement': lambda match, context: self._normalize_user_home(match, context)
            },
            'worktree_normalization': {
                'description': 'Normalize worktree directory names to generic pattern',
                'patterns': self.platform_patterns['worktree_names'],
                'replacement': lambda match, context: self._normalize_worktree_name(match, context)
            },
            'path_separator_fixing': {
                'description': 'Convert Windows backslashes to forward slashes',
                'patterns': self.platform_patterns['path_separators'],
                'replacement': lambda match, context: match.group(0).replace('\\', '/')
            },
            'project_root_relative': {
                'description': 'Convert absolute project paths to relative paths',
                'patterns': self.platform_patterns['absolute_project_paths'],
                'replacement': lambda match, context: self._make_relative_to_project(match, context)
            },
            'temp_path_generic': {
                'description': 'Normalize temp directory paths to use tempfile module',
                'patterns': self.platform_patterns['temp_directory_paths'],
                'replacement': lambda match, context: self._normalize_temp_path(match, context)
            }
        }

    def _normalize_user_home(self, match: re.Match, context: dict) -> str:
        """Normalize user home paths to relative paths or environment variables."""
        matched_text = match.group(0)

        # If this is in a test file, prefer relative paths
        if context.get('file_type') == 'test':
            return ''  # Remove the home path prefix, making it relative
        # For config files or scripts, use environment variable
        return '${HOME}/'

    def _normalize_worktree_name(self, match: re.Match, context: dict) -> str:
        """Normalize worktree names to a generic pattern."""
        matched_text = match.group(0)

        # Extract the basic pattern
        if 'worker' in matched_text.lower():
            return '/worktree_main/'
        if 'test' in matched_text.lower():
            return '/worktree_tests/'
        return '/worktree/'

    def _make_relative_to_project(self, match: re.Match, context: dict) -> str:
        """Convert absolute project paths to relative paths."""
        matched_text = match.group(0).strip('\'"')

        try:
            # Try to make the path relative to project root
            abs_path = Path(matched_text)
            project_path = Path(self.project_root)

            if project_path in abs_path.parents or abs_path == project_path:
                relative = abs_path.relative_to(project_path)
                return f'"{relative}"' if '"' in match.group(0) else f"'{relative}'"
        except (ValueError, OSError):
            pass

        # Fallback: use environment variable or placeholder
        return '"${PROJECT_ROOT}"' if '"' in match.group(0) else "'${PROJECT_ROOT}'"

    def _normalize_temp_path(self, match: re.Match, context: dict) -> str:
        """Normalize temp directory paths to use portable patterns."""
        matched_text = match.group(0)

        # If this looks like a test temp directory, use tempfile pattern
        if context.get('file_type') == 'test':
            return 'tempfile.mkdtemp() + "/"'
        return '"${TMPDIR}"'

    def scan_test_file_for_issues(self, file_path: str) -> dict[str, list[dict]]:
        """Scan a test file for platform-specific path issues.

        Returns:
            Dict with issue categories and details
        """
        issues_found = {
            'user_home_paths': [],
            'worktree_names': [],
            'path_separators': [],
            'absolute_project_paths': [],
            'temp_directory_paths': []
        }

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

            # Check each line for issues
            for line_num, line in enumerate(lines, 1):
                for issue_type, patterns in self.platform_patterns.items():
                    for pattern in patterns:
                        matches = pattern.finditer(line)
                        for match in matches:
                            issues_found[issue_type].append({
                                'line_number': line_num,
                                'line_content': line.strip(),
                                'matched_text': match.group(0),
                                'start_pos': match.start(),
                                'end_pos': match.end(),
                                'suggested_fix': self._suggest_fix(issue_type, match, line)
                            })

        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")

        return issues_found

    def _suggest_fix(self, issue_type: str, match: re.Match, line: str) -> str:
        """Suggest a fix for a specific issue."""
        context = {'file_type': 'test'}  # Assume test context for suggestions

        if issue_type in self.normalization_rules:
            rule = self.normalization_rules[issue_type]
            try:
                suggestion = rule['replacement'](match, context)
                return suggestion
            except Exception:
                pass

        return f"[Fix needed for {issue_type}]"

    def fix_test_file_paths(self, file_path: str, dry_run: bool = False) -> dict[str, bool | int | list]:
        """Fix path issues in a test file.

        Returns:
            Dict with fix results and statistics
        """
        result = {
            'success': False,
            'fixes_applied': 0,
            'backup_created': False,
            'changes': []
        }

        try:
            # Read the file content
            with open(file_path, encoding='utf-8') as f:
                original_content = f.read()

            # Track changes
            modified_content = original_content
            changes_made = []

            # Apply each normalization rule
            context = {
                'file_type': 'test',
                'file_path': file_path
            }

            for rule_name, rule_config in self.normalization_rules.items():
                for pattern in rule_config['patterns']:
                    matches = list(pattern.finditer(modified_content))

                    # Process matches in reverse order to preserve positions
                    for match in reversed(matches):
                        try:
                            replacement = rule_config['replacement'](match, context)

                            # Apply the replacement
                            start, end = match.span()
                            new_content = (modified_content[:start] +
                                         replacement +
                                         modified_content[end:])

                            if new_content != modified_content:
                                changes_made.append({
                                    'rule': rule_name,
                                    'original': match.group(0),
                                    'replacement': replacement,
                                    'line_estimate': modified_content[:start].count('\n') + 1
                                })
                                modified_content = new_content

                        except Exception as e:
                            logger.warning(f"Failed to apply {rule_name} fix: {e}")

            # If changes were made and not dry run, write the file
            if changes_made and not dry_run:
                # Create backup
                backup_path = file_path + '.bak'
                if not os.path.exists(backup_path):
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    result['backup_created'] = True

                # Write the modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)

                result['success'] = True

            result['fixes_applied'] = len(changes_made)
            result['changes'] = changes_made

            if changes_made:
                logger.info(f"Fixed {len(changes_made)} path issues in {file_path}")
                for change in changes_made:
                    logger.debug(f"  {change['rule']}: '{change['original']}' -> '{change['replacement']}'")

        except Exception as e:
            logger.error(f"Failed to fix paths in {file_path}: {e}")

        return result

    def find_test_files_with_path_issues(self, search_patterns: list[str] = None) -> list[str]:
        """Find test files that likely have path issues.

        Args:
            search_patterns: Glob patterns to search for test files

        Returns:
            List of test file paths that have potential issues
        """
        if not search_patterns:
            search_patterns = [
                'tests/**/test_*.py',
                'test_*.py',
                '**/tests/test_*.py',
                'mvp_site/tests/test_*.py',
                'scripts/tests/test_*.py',
                'orchestration/tests/test_*.py',
                '.claude/hooks/tests/test_*.py'
            ]

        problematic_files = []
        project_path = Path(self.project_root)

        for pattern in search_patterns:
            try:
                for test_file in project_path.glob(pattern):
                    if test_file.is_file():
                        issues = self.scan_test_file_for_issues(str(test_file))

                        # Check if file has any issues
                        total_issues = sum(len(issue_list) for issue_list in issues.values())
                        if total_issues > 0:
                            problematic_files.append(str(test_file))
                            logger.debug(f"Found {total_issues} path issues in {test_file}")

            except Exception as e:
                logger.warning(f"Error searching pattern {pattern}: {e}")

        logger.info(f"Found {len(problematic_files)} test files with path issues")
        return problematic_files

    def generate_path_compatibility_report(self, test_files: list[str]) -> dict:
        """Generate a comprehensive report of path compatibility issues.

        Returns:
            Dict with detailed analysis of path issues across test files
        """
        report = {
            'summary': {
                'total_files_scanned': 0,
                'files_with_issues': 0,
                'total_issues_found': 0
            },
            'issue_breakdown': {
                'user_home_paths': 0,
                'worktree_names': 0,
                'path_separators': 0,
                'absolute_project_paths': 0,
                'temp_directory_paths': 0
            },
            'file_details': [],
            'recommended_fixes': []
        }

        for file_path in test_files:
            if not os.path.exists(file_path):
                continue

            report['summary']['total_files_scanned'] += 1
            issues = self.scan_test_file_for_issues(file_path)

            file_issue_count = sum(len(issue_list) for issue_list in issues.values())
            if file_issue_count > 0:
                report['summary']['files_with_issues'] += 1
                report['summary']['total_issues_found'] += file_issue_count

                # Update issue breakdown
                for issue_type, issue_list in issues.items():
                    report['issue_breakdown'][issue_type] += len(issue_list)

                # Add file details
                relative_path = os.path.relpath(file_path, self.project_root)
                report['file_details'].append({
                    'file_path': relative_path,
                    'issue_count': file_issue_count,
                    'issues': issues
                })

        # Generate recommended fixes
        report['recommended_fixes'] = self._generate_fix_recommendations(report)

        return report

    def _generate_fix_recommendations(self, report: dict) -> list[dict]:
        """Generate recommended fix strategies based on the report."""
        recommendations = []
        issue_breakdown = report['issue_breakdown']

        if issue_breakdown['user_home_paths'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'user_home_paths',
                'issue_count': issue_breakdown['user_home_paths'],
                'description': 'Replace absolute user home paths with relative paths or environment variables',
                'command': 'python3 scripts/test_path_normalizer.py --fix-paths --rule user_home_replacement'
            })

        if issue_breakdown['worktree_names'] > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'worktree_names',
                'issue_count': issue_breakdown['worktree_names'],
                'description': 'Normalize worktree directory names to generic patterns',
                'command': 'python3 scripts/test_path_normalizer.py --fix-paths --rule worktree_normalization'
            })

        if issue_breakdown['absolute_project_paths'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'absolute_project_paths',
                'issue_count': issue_breakdown['absolute_project_paths'],
                'description': 'Convert absolute project paths to relative paths',
                'command': 'python3 scripts/test_path_normalizer.py --fix-paths --rule project_root_relative'
            })

        if issue_breakdown['path_separators'] > 0:
            recommendations.append({
                'priority': 'low',
                'category': 'path_separators',
                'issue_count': issue_breakdown['path_separators'],
                'description': 'Fix Windows backslash path separators',
                'command': 'python3 scripts/test_path_normalizer.py --fix-paths --rule path_separator_fixing'
            })

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return recommendations


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Normalize test file paths for cross-platform compatibility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scan-all                                     # Find all files with path issues
  %(prog)s --fix-paths test_broken.py                     # Fix specific test file
  %(prog)s --fix-paths test_*.py --dry-run                # Preview fixes
  %(prog)s --generate-report --output-file report.json   # Generate comprehensive report
  %(prog)s --from-failure-list failing_tests.txt         # Fix files from failure list
        """
    )

    parser.add_argument(
        "--scan-all", action="store_true",
        help="Scan all test files for path issues"
    )
    parser.add_argument(
        "--fix-paths",
        help="Fix path issues in specified test files (glob pattern supported)"
    )
    parser.add_argument(
        "--from-failure-list",
        help="Read test file list from failure list file"
    )
    parser.add_argument(
        "--generate-report", action="store_true",
        help="Generate comprehensive path compatibility report"
    )
    parser.add_argument(
        "--output-file",
        help="Output file for reports (JSON format)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be fixed without making changes"
    )
    parser.add_argument(
        "--rule",
        choices=['user_home_replacement', 'worktree_normalization',
                'path_separator_fixing', 'project_root_relative', 'temp_path_generic'],
        help="Apply only specific normalization rule"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize normalizer
        normalizer = PathNormalizer()

        if args.scan_all:
            # Find all problematic files
            problematic_files = normalizer.find_test_files_with_path_issues()

            print(f"\nFound {len(problematic_files)} test files with path issues:")
            for file_path in problematic_files:
                rel_path = os.path.relpath(file_path, normalizer.project_root)
                print(f"  - {rel_path}")

                if args.verbose:
                    issues = normalizer.scan_test_file_for_issues(file_path)
                    for issue_type, issue_list in issues.items():
                        if issue_list:
                            print(f"    {issue_type}: {len(issue_list)} issues")

        elif args.fix_paths:
            # Fix paths in specified files

            if args.from_failure_list:
                # Read files from failure list
                with open(args.from_failure_list) as f:
                    test_files = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            else:
                # Use glob pattern
                test_files = glob(args.fix_paths)

            if not test_files:
                logger.error("No test files found matching the pattern")
                sys.exit(1)

            print(f"Processing {len(test_files)} test files:")

            total_fixes = 0
            successful_fixes = 0

            for file_path in test_files:
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue

                result = normalizer.fix_test_file_paths(file_path, dry_run=args.dry_run)

                if result['fixes_applied'] > 0:
                    status = "would fix" if args.dry_run else "fixed"
                    print(f"  ✅ {status} {result['fixes_applied']} issues in {os.path.basename(file_path)}")
                    successful_fixes += 1
                    total_fixes += result['fixes_applied']

                    if args.verbose:
                        for change in result['changes']:
                            print(f"    - {change['rule']}: line {change['line_estimate']}")
                else:
                    print(f"  ✓ No issues found in {os.path.basename(file_path)}")

            action = "Would fix" if args.dry_run else "Fixed"
            print(f"\n{action} {total_fixes} path issues across {successful_fixes} files")

        elif args.generate_report:
            # Generate comprehensive report
            test_files = normalizer.find_test_files_with_path_issues()
            report = normalizer.generate_path_compatibility_report(test_files)

            # Output report
            if args.output_file:
                import json
                with open(args.output_file, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"Report saved to {args.output_file}")

            # Print summary
            print("\nPath Compatibility Report:")
            print(f"  Files scanned: {report['summary']['total_files_scanned']}")
            print(f"  Files with issues: {report['summary']['files_with_issues']}")
            print(f"  Total issues: {report['summary']['total_issues_found']}")

            print("\nIssue breakdown:")
            for issue_type, count in report['issue_breakdown'].items():
                if count > 0:
                    print(f"  {issue_type}: {count}")

            print("\nRecommended fixes:")
            for rec in report['recommended_fixes']:
                print(f"  [{rec['priority'].upper()}] {rec['description']} ({rec['issue_count']} issues)")
                print(f"    Command: {rec['command']}")

        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        logger.error(f"Path normalization failed: {e}")
        sys.exit(1)


class TestPathNormalizerCompatibility(unittest.TestCase):
    """Test compatibility for CLI tool."""

    def test_can_instantiate_normalizer(self):
        """Test that the path normalizer can be instantiated."""
        normalizer = PathNormalizer()
        self.assertIsNotNone(normalizer)

if __name__ == "__main__":
    # Check if this is being run as a test (no command line arguments)
    if len(sys.argv) == 1:
        # Run as unittest when no arguments provided
        unittest.main(verbosity=0, exit=False)
    else:
        # Run as CLI tool when arguments provided
        main()
